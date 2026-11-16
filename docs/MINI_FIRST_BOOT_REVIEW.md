# Review of the first MINI flash and boot

Offline review dated November 15, 2026, with no device commands or changes to
the plan, guard or frozen artifacts. The reviewed candidate is
`build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin`, 516096 bytes,
SHA256 `3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
The `firmware-manifest.json` manifest has SHA256
`f119ab571a6cb04c8ca72513b5d18d614e079e756d209ce5794fbaeb4fe77d12`.
This document does not attest to installation or recovery from an already
installed app.

The main finding concerns interruption during replacement.
[plan_mini_install.py](../tools/plan_mini_install.py) orders changed sectors
from `0x5000` onward and leaves `0x4000` until last. SPL verifies headers,
not the CRC of the entire application body: at `0x01C033E2`, the CRC covers
30 bytes, compared with the header's first two bytes. Until the final write,
valid MINI headers and entry therefore remain alongside a partially G body.
An interruption may execute mixed code without reaching the new guard.
The label `power_loss_atomicity_proven=false` is correct; writing the header
sector last does not by itself eliminate this window.

Within the final sector, ascending page order would also publish the header
at `0x4000` before the entry at `0x4120` and hook at `0x418A`.
The decision for the new operational installer is to program
`0x4100..0x4F00` first and **page `0x4000` last**, verifying every page
and the sector. Pre-erase staging/echo can use `0x4100`. The current HYW core
accepts aligned pages not yet present in the bitmap and therefore permits
this order. The change narrows the final window but does not resolve the
earlier window with the old header. As of this review, the new installer
still needs review: this policy is not attributed to the frozen plan.

Initial invalidation is not added automatically. The original UltraRig
installer's `_write_plan`, in the recovered disassembly from line 29190,
moves the header to the end and first writes an FF sector; the call appears
at bytecode offsets 434..460. This is a real original policy, but its TANK-G
fallback does not prove the MINI's physical fallback.

The reviewed MINI SPL, SHA256
`fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d`,
clears `app_base` at `0x01C04D68` when the header fails.
The scan path at `0x01C04E26` can select the physical backup's OTA request
at `0xBCF00` and its `LOADER.BIN` at `0xB7000`.
After decompression and CRC verification, the indirect call at `0x01C04F64`
enters the loader at `0x01C0A800`. Only if the loader returns or fails,
and `app_base` remains zero, does branch `0x01C04F94..4F98` lead to the
ROM marker/reset at `0x01C0529A`. This does not mean “an invalid header
immediately implies a ROM disk.”

The local copy `analysis/tank-mini/ota.bin` (SHA256
`9c62bbdfd55f6527a3cffe43abc16c621d0900a8ff47685240abb1ee596eb66e`)
was decoded exclusively in memory. The payload installed in the backup
already matches the package payload, as verified by
[audit_mini_boot_contract.py](../tools/audit_mini_boot_contract.py).
The internal header identifies `usb_hid_ota.bin`. Decoding follows LZ4
blocks with the preceding dictionary, as in
[core_lz4_block/core_updater_decode](../upstream/m-bootloader/src/core.c):

| Block | Compressed bytes | Produced bytes |
|---|---:|---:|
| 1 | 3209 | 4096 |
| 2 | 3550 | 4096 |
| 3 | 3568 | 4096 |
| 4 | 3613 | 4096 |
| 5 | 3464 | 4096 |
| 6 | 2442 | 2844 |

Total: 23324 bytes, CRC16 `0x6A00` matching the header, decompressed SHA256
`4758c7452f8527af9d479db9cc766a6c07d592e255633b593363f6ea1de73c97`.
This verifies content and the loading branch without running the updater.
No existing trial shows OTA enumeration after invalidating a MINI header,
an OTA→ROM command, or automatic stock restoration without a host.
The loader contains references to `flash.bin` and `uboot.boot`:
it must not be treated as an application-only writer.
The HYW/ROM resume protocol cannot be claimed to apply to that OTA device.
Initial invalidation therefore remains excluded, and write interruption
remains a stated limitation.

Independent candidate checks compared decoded bytes with G and the guard
payload without invoking the builder:

| Region | Result |
|---|---|
| G entry `0x02000120..124` | `14948000`, identical to the original |
| Hook `0x0200018A..196` | `c3ea1db90000000000000000`, jump to the guard |
| Guard v2 `0x020773C8..0x020774F2` | Exactly 298 bytes, SHA256 `fed49e2b7df48f652b791d3bf52c851fae9d02ce3b21363996cd28e75ac99291` |
| G P33 release `0x02000EE0..0x02000FB6` | Identical to the original |
| P33 caller `0x020011C2..0x020011D2` | Identical, including call to `0x02000EE0` |
| RAM P33 writer, LMA `0x0205768C..0x020576CA` | Identical to the original |

This candidate's guard manifest has SHA256
`7477a0a10ae9ad7c5459432535873eb05105dc9b1065c76a1eb6f1c7cd4ca729`.
The preserved SPL clears P33 latches D0..DF/AD..AF before handover.
The v2 prefix sets DIR for PA10/PA0/PA3 before the callable, preserves the
G context on the normal branch, and does not depend on an inherited input
direction. No new guard bounds/ABI defects were found. The already recorded
physical HYK1 trial covers released→held→released and marker/reset→new ROM;
it does not prove the XIP prefix, cold-boot mux or complete G execution.

Review of the frozen writer found no NOR path outside
`[0x4000,0x82000)`: `hyw_range` checks endpoints first, then
`length <= end-address`; erase4K and program256 recheck range and alignment
in the PIO driver before emitting the 24-bit address. The core restricts
each page to the armed sector and bitmap. SPL/config, VM/OTA, BTIF, USR and
key_mac remain excluded. The target gate is still zero;
this conclusion does not qualify a future enabled build or its client.

The initial rollback finding was that the current plan accepts the stock
backup as its preimage and the `tankm` app as its destination.
After a complete or partial write, those constraints do not describe the
reverse direction. An explicit, separate restoration path is needed to
acquire and retain the current preimage in ROM and rewrite stock bytes within
the same allowlist. Automatic rollback on error is not required;
deliberate restoration after returning to ROM must be possible.
The guard and rollback file alone do not already constitute that procedure.
This finding is now addressed by
[restore_mini_stock.py](../tools/restore_mini_stock.py) and 16 tests:
the separate factory also accepts an incomplete app, pins the current read's
bytes, verifies SPL/key_mac, and prepares the stock direction without writing
external regions. The API and limits are in
[MINI_STOCK_RESTORATION.md](MINI_STOCK_RESTORATION.md).

Sources read during this review:

| File | SHA256 |
|---|---|
| `tools/plan_mini_install.py` | `1c99f931789e8ef79feef43ab50472af22f65eb8468f6884aac16c3e7a715a64` |
| `tools/build_mini_app_writer.py` | `39941618458365ca9c151a33e468a8b83e531f700fd7bfb3aedb581dd61c2ec2` |
| `firmware/mini/app_writer/writer.c` | `f43e42b4d0aec8b354ac7f02a1067b22d3e978bd81d4412a9471f01e18086de2` |
| `firmware/mini/app_writer/nor_pio.c` | `a31813c4e71d232b62f0c29f0bd40c4fc923c40f8c672faa7d205f0ee8ec4dab` |

Checks belong to different phases:

| Phase | Required or obtainable evidence |
|---|---|
| Before writing | Pinned candidate and sources; complete backup from the same unit; fresh read/preimage; JEDEC/status; bounded writer and host that reject ambiguous retries; RAM staging/echo and stack; distinct return slot known not to be live. HYK1 has already qualified buttons and marker/reset. |
| During writing | Erase/program results, WIP waits, exact page/sector readback, complete area matching the candidate and preserved external regions. An error does not authorize resetting the partial app or automatic retries. |
| After verified installation | First reset with all three buttons held before reset: observe new ROM enumeration and INQUIRY, then qualify the XIP prefix. Only after release and another normal boot: `tankm_fw` PONG, stability, audio, app and presets. |

XIP-guard execution and recovery from a hang of the installed app are checks
performed after installation; requiring them as completed hardware evidence
before the first flash would be circular. A first boot with every footswitch
held tests the recovery branch before starting the G RTOS, drivers and DSP.
It does not protect against damaged header/entry/guard data or guarantee
success after an interrupted installation. Incomplete trials leave the
corresponding hardware flags false.

The subsequent review of operational installer `tools/install_mini_app.py`,
SHA256 `4a85b608c052a870a322d1bd57653b167b33223f5a2a65338cbc9b5aa031f22f`,
found no additional blockers in tokens/sequences, staging/echo, bounds,
preimage/readback or journaling before commands. The pinned operational
manifest is `214cbfc3c14d4bc2eff83a9e88ae8b9f9232c211c685e81af9059b182f05031c`.
The target derivation enables the gate and increases only the WIP polling
delay from 256 to 768 iterations; the gate0 writer remains unchanged.
Polling bounds are finite but are not physical timing qualification:
a host timeout remains terminal and ambiguous, without automatic retry or reset.

Root's runners `analysis/hardware/run_mini_first_install.py` and
`run_mini_first_boot.py` were also read, without execution.
The readerB→writerA→readerB sequence preserves the distinction between
an active slot and an ambiguous jump; it compares 1 MiB before and after
and leaves ROM active. Held/released resets are separate, with a new arrival
and INQUIRY for held, and CDC observation for released.
That last observation is not yet a handshake: the original UltraRig installer
sends PING as soon as CDC appears to confirm boot. PING/INFO and subsequent
stability checks must therefore promptly follow enumeration.
Software reset through SPL and a real power cycle remain separate trials.
