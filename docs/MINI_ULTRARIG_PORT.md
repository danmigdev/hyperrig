# Complete UltraRig G → HyperRig MINI port

The base candidate retains the code of the **entire UltraRig G
v2 M5.71 application**: 485,772 bytes, including the audio engine, OS, USB, BLE,
preset management, and original drivers. Preserving the binary components
does not demonstrate that each function works correctly on MINI hardware.
It does not incorporate the stock MINI application. The stock package and
the individual unit's backup serve to reconstruct hardware, boot, and partitions.

This document describes the base formatter and its **offline artifact,
incomplete for the hardware**, identified by the hash below. The formatter
neither installs nor boots the firmware, and this audit does not access the pedal.
The subsequent integrated candidate, with board adaptations, and the physical
trials have separate artifacts and reports: see the
[integrated build](MINI_INTEGRATED_PORT.md) and [project status](../README.md).

```powershell
python -X utf8 tools/audit_mini_ultrarig_port.py
```

The command generates:

* `build/mini-ultrarig/hyperrig-mini-g-derived.app.bin`: a 516,096-byte
  application area, SHA-256
  `4e74d0c0b1c1f491afdaa92e441d4504efcaff4237b4af1706e57a6e434a20ab`;
* `research/mini-ultrarig-port.json`: provenance, instructions, patches,
  directory, NOR comparisons, limitations, and reproducible checks.

The candidate contains the MINI directory, five identity/branding patches,
and one VM geometry patch. Each patch checks the original bytes before
changing them. Reversing only these patches recovers the original G
`app.bin` exactly. All JLFS CRCs are recalculated and verified
after a fresh SFC decode. The report retains `flashable=false`,
`board_port_complete=false`, and `boot_verified_on_mini=false`.

## Format and space

| Property | UltraRig G v2 | Stock MINI 009 |
|---|---:|---:|
| SoC/format | AC791N, pi32v2, SFC/JLFS | AC791N, pi32v2, SFC/JLFS |
| Application key verified by CRCs | `0x980F` | `0x980F` |
| Physical application area | `[0x4000,0x7B000)` | `[0x4000,0x82000)` |
| Area size | `0x77000` | `0x7E000` |
| `app.bin` offset within the area | `0x120` | `0x120` |
| CPU entry | `0x02000120` | `0x02000120` |
| `app.bin` | 485,772 bytes | 511,032 bytes |
| `cfg_tool.bin` | 383 bytes | The same 383 bytes |

The format and space are compatible; this does not demonstrate electrical
compatibility or compatible initialization parameters. The MINI area provides
28,672 bytes more than the G package. Considering the actual end of the files,
the maximum space for additional code is **29,653 bytes**, before any
alignment. Code can start at `0x02076AAC`; `cfg_tool.bin` is
moved after it and its JLFS entry updated. G opens this file
through `mnt/sdfile/app/cfg_tool.bin` in fragment `0x0201FAB8..1FAF6`.

This space belongs to the application being replaced. The builder does not
occupy empty flash in data partitions and does not produce a complete
image of the 1 MiB unit or an FWSC container.

## Bootloader and RAM

The original UltraRig installer distributes an **application area**, not
a new persistent bootloader. The recovered `build_target` bytecode,
source lines 1623–1652, copies the current dump and replaces `APP_AREA`.
SPL remains unchanged; the default USR policy is `keep`. There are separate
branches for VM migration on G97/Tank-B firmware, repair, and restoration:
it is incorrect to claim that every installer operation writes only the
application. The `wl82loader.bin` loader runs in RAM. The original
package does not declare MINI support.

Retaining the MINI factory bootloader is therefore consistent with
the UltraRig architecture; the factory application is replaced entirely.
Full compatibility of the handover remains to be demonstrated.

| Reconstructed G region or register | Value |
|---|---|
| Initial RAM copy | `[0x01C00000,0x01C2030C)` from `0x02056780` |
| BSS | `[0x01C2030C,0x01C38050)` |
| Initial SP / SSP | `0x01C350B8` / `0x01C360B8` |
| USP / CPU1 SP | `0x01C363B8` / `0x01C373B8` |
| Heap | `[0x01C38060,0x01C7FBA0)`, 293,696 bytes |
| External copies/clears required by reset | Zero bytes |
| Private copy of G boot context | `0x01C7FD4C` |

The reset and heap fit within the 512 KiB internal RAM. This does not prove
the absence of every other external RAM access. The slots used by the ROM
probes do not remain free: they fall within allocations of the complete application.

The MINI bootloader passes `r0=0x01C7FE08`. G also reads eight bytes at
`r0+80` and four at `r0+88`, at sites `0x0200045C` and `0x0200046A`.
Correct initialization of these extensions in the MINI path without
SDRAM has not yet been demonstrated. This is a remaining handover check,
separate from the valid stock bootloader CRCs.

## Partitions: directory, geometry, and content

| Name | Original G | MINI candidate |
|---|---|---|
| VM | `[0x7B000,0xBD000)` | `[0x82000,0xBE000)` |
| PRCT | `[0,0x7B000)` | `[0,0x82000)` |
| BTIF | `[0xBD000,0xBE000)` | `[0xBE000,0xBF000)` |
| OTP | `[0xBE000,0xBF000)` | Entry removed, absent on MINI |
| USR | `[0xBF000,0xFF000)` | Identical |

The partitions are derived from the original directories, with verified CRCs.
Blindly retaining the G OTP entry would make it overlap MINI BTIF.
The builder uses only MINI partition headers and explicitly records
OTP removal. It does not copy or rewrite VM/BTIF/USR/key_mac contents.

The G access evidence is separate for each partition:

* **VM:** loop `0x02022208..0x0202225A` compares the name `vm`
  (`0x02035851`) with JLFS entries, loads the offset and size, and passes
  the metadata through ioctl205. The base is not simply fixed at `0x7B000`.
* **BTIF:** `mnt/sdfile/app/btif` is opened at `0x0201FB00`, followed by
  metadata reads and access to base+512 for configuration. The new
  position is therefore represented by the directory in this path.
* **USR:** `0xBF000` is also hardcoded; function `0x020026BA` returns
  slot positions, with special cases `0xDD000` and `0xDE000`.
  These addresses remain unchanged.
* **OTP:** no `OTP` string occurs inside `app.bin`; its only occurrence
  in the G area is the directory name. This search **does not prove**
  the absence of indirect access, access by index, or access to NOR security
  registers. Hardware NOR OTP and the JLFS partition named OTP are different
  objects. Compatibility of all consumers remains an open gate.

The physical VM declared in the directory is larger than the actual banks
used by the SDK. G limits the active part to 64 KiB, two 32 KiB banks;
stock MINI limits NOR to 16 KiB, two 8 KiB banks. The candidate changes
only the pair of G immediates:

| CPU | Before | After |
|---|---|---|
| `0x0202067E` | `20 e9 80 0b`: `if (r0 >= 65536)` | `20 e9 80 0c`: `if (r0 >= 16384)` |
| `0x02020682` | `60 e0 80 0b`: `r0 = 0x10000` | `60 e0 80 0c`: `r0 = 0x4000` |

The change is re-encoded from the pinned ISA table: only the immediate
fields change, preserving the register, predicate, and length. MINI reset
starts VM initialization with NOR limit 16384 in fragment
`0x0201FD72..0x0201FD9C`.

In the frozen backup, SHA-256 `72db5e70…5f8a180`, bank B at `0x84000`
contains 134 records with valid CRCs; write pointer `0x8531E`, usage 59.7412%.
The other bank and the tail are erased. The parser reconstructed from the
installer's `vm_state`/`vm_entries` rules requires no maintenance with MINI
geometry. With G geometry and only the new base, both headers are `FF`:
formatting would be requested. **No VM migration is necessary to correct
this geometry mismatch.**

This evidence does not interpret the meaning of each ID, radio calibration,
or the USR preset format. It does not make the backup state permanent:
a future candidate must recheck the current VM. The G firmware retains
its guard against writes outside USR.

## NOR driver

Sixteen original G/MINI fragments match after explicitly normalizing
call targets, two globals, and local jump destinations. MMIO, masks,
registers, instruction order, and opcodes remain part of the comparison.
The report retains ranges and hashes of the normalized fragments.

| Function | G | MINI |
|---|---|---|
| CS PD0 | `0x01C00088` | `0x01C0008A` |
| SPI reads by mode | `0x01C00290` | `0x01C00288` |
| JEDEC9F + UID4B | `0x01C0044C` | `0x01C00500` |
| Status read 05/35 | `0x01C004D0` | `0x01C00678` |
| Busy wait 05 | `0x01C00600` | `0x01C005A4` |
| Erase dispatcher | `0x01C00640` | `0x01C005E4` |
| Status write 01/31 | `0x01C006D2` | `0x01C006B2` |
| Status update policy | `0x01C0079E` | `0x01C0077E` |
| Page program 02 | `0x01C00840` | `0x01C00820` |

The JEDEC ID physically observed by the separate reader, `EB6014`, also
produces 1 MiB in the G algorithm: final byte `0x14`, exponent minus 16,
power of 2, and shift by 16 at `0x02002746..0x02002750`. The compared fragments
introduce no rejection specific to manufacturer EB.
The original installer bytecode also lists `EB6014` among accepted
`ALT_FLASH_IDS`; this does not extend its support to the MINI model.
Status/QE sequences are also shared; programming them has not been tested
on the chip. Opcodes are described here for audit purposes: the tool
does not send them or expose any hardware interface.

The following remain separate: lock/CPU1 behavior, cache invalidation called
by the driver, SFC timing under the G clock policy, the origin of status-change
requests, and all paths not compared. Fragment equivalence does not amount
to an erase/program or recovery test on MINI.

## Identity and formatter for integration

The version strings retain `M5.71 rel ble` and the original date, with
the `tankm_fw` prefix. The PONG format remains `PONG %s %s %s%s\n`. The two
version preimages are at `0x0203678E` and `0x020370E8`. The ASCII brands
are at `0x0203614A` and `0x0203A123`; the complete UTF16 USB descriptor at
`0x0203A264` changes from `Tank-G UltraRig` to `Tank-M HyperRig`, still 32 bytes.
The internal diagnostic names `tankg_audio`/`tankg_core1` are not MINI markers.
Original sources and provenance NOTICE files are preserved.

The importable API is:

```python
from audit_mini_ultrarig_port import BinaryPatch, compose_candidate

area, report = compose_candidate(g_original_bytes, mini_fwsc_bytes)
# For future integration of already verified board code:
area, report = compose_candidate(
    g_original_bytes, mini_fwsc_bytes,
    additional_patches=tuple(patches_with_exact_preimages),
    append_code=blob_board,
)
```

Each additional patch must lie within the original portion of `app.bin`,
have the same length, and not overlap the base patches. The appended blob
preserves all G addresses, moves cfg, and updates CRCs/headers. The formatter
does not establish the semantic validity of supplied patches; all usability
flags remain false.

Checks cover the SFC/JLFS roundtrip, inverse comparison of the entire
application, six rejections for input/preimage/overlap/bounds/CRC, an append
test with relocated cfg, and rejection of a corrupt VM record.
An in-memory-only substitution in the backup also demonstrates that the
bootloader and every byte from `0x82000` onward remain identical; that
complete candidate dump is not written to a file.

## Steps beyond the base formatter

These items describe the work required beyond the base artifact in
this document. Current integration and physical-trial status is reported
in the README and specific reports, without retroactively promoting
the hardware validity of this formatter.

1. Integrate the MINI codec/pin/mute sequence into the complete G firmware,
   then map physical controls and LEDs; use the separate board audit as evidence.
2. Resolve handover, clock/SFC, OTP consumers, and BTIF/VM calibration.
3. Demonstrate recovery with a corrupt application: the already successful
   return from ROM to intact stock does not constitute this proof.
4. Verify complete application boot, USB/BLE PONG, audio, preset loading
   and saving, stable reboot, and prolonged operation.

Reconstructing everything in C remains a larger undertaking: the public
UltraRig sources distribute binaries; local decompiled C is partial and is
not a complete, rebuildable source tree. The binary port preserves the original
components without reconstructing all of them in C; their presence does not
equal verification of their functions on MINI. Hardware adaptations, physical
controls, audio, and app operations require their own tests.
