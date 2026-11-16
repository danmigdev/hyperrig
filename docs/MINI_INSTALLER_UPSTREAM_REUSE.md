# Reusing the UltraRig installer for a portable MINI installer

This is an offline audit of the recovered UltraRig installer and the MINI
installation paths already exercised on the user's unit. No original installer,
browser, device command, or flash operation was run for this audit. The workflow
below is an implementation recommendation, not a newly qualified installer.

The shortest practical route is an English HyperRig installer around the
existing MINI transport, reader, writer, and verification code. Reuse the
original installer's separation of install/update/restore, preflight, mandatory
backup, progress reporting, and failure states. Do not run or lightly rebrand
the G/B installer against a MINI.

## Evidence and source locations

The local original is the alpha11 v2 Windows package extracted into
`recovered/installer/`. Its manifest records Python 3.12 bytecode and explicitly
records that extraction used parsing and disassembly only. Complete original
Python source files have not been recovered.

| Source record | SHA-256 |
|---|---|
| `tankg_install.marshal` | `3ce94472c774cfa573cd1c51a7ce1ca54620a8ef1d201b9a450975619fcb268b` |
| `tankg_install.dis.txt` | `1a2a94103d3d0ee80deefd6820c2d602d41b9e20a6e101855b94a6100bbc170c` |
| `ultrarig_installer_gui.marshal` | `dc15784f715ba66ca06f4bf5e76e5991c8b912771e5b20be576ee3e9747b27a6` |
| `ultrarig_installer_gui.dis.txt` | `085cfe49feece03dbeb5260bd436fde6b2b4a9e36fe724d06a7141c690d17bc7` |

The function locations below use the original Python line numbers printed in
the disassembly. They are not line numbers in recovered `.py` files. The
[provenance and license requirements](PROVENANCE.md) still apply to derived
installer work; changing product names does not replace those requirements.

Actual MINI evidence includes:

- [First installation verification](../research/mini-final-install-independent.json),
  SHA-256 `e8e8f09309a037c57ab32051502922ea88bb0b9091761863d29cd3c2c1b7e558`:
  the completed application and preserved external regions were independently
  checked after the interrupted installation was resumed.
- [PC-limit upgrade verification](../research/mini-pc-limit-install-independent.json),
  SHA-256 `8c2636ad3acf04e3e95d1622bc989f62ae1e558425c875e3c7f2b731cad13716`:
  the later v3 application update changed only sector `0x4000` and independently
  checked a fresh full NOR read before and after writing.

These records prove operations on that unit and those artifacts. They do not
establish compatibility with every MINI revision or a packaged installer on
another computer.

## Original patterns worth retaining

| Original function / original line | Evidence and reusable behavior | MINI implementation to use |
|---|---|---|
| `preflight_resources`, 3691; `preflight_out`, 3713; `write_verified`, 3740 | Validate bundled loader/reset hashes and imports, then check that the backup directory is writable, durable, readable, and has space before entering ROM. | Package verification before device mode changes; use `tools/mini_host_journal.py` for durable JSON and shared-delete reads. |
| `RealPedal.identify`, 2917; `send_soft_key`, 2956 | Reidentify immediately before sending the soft key; reject ambiguous MIDI ports, an unexpected identity, or an already connected ROM/CDC device. | `hyperrig/device.py:ReadOnlyMini` and `hyperrig/mini.py` provide the stock identity/read protocol. Add a dedicated reviewed entry action around them rather than expanding the read-only class. |
| `RealPedal.cdc_cmd`, 3163; `goto_uboot_from_tankg`, 5124 | Require a real PONG before `UBOOT`, close the application port, then wait for a ROM device. | `tools/probe_mini_app_cdc_handshake.py:identify` for the bounded native CDC handshake; `tools/enter_mini_rom_webserial.py` and `tools/audit_mini_cdc_recovery.py` document the actual command and observed transition. Rework the historical entry helper's session-specific inputs for a new installer. |
| `Guard.execute`, 2505; `UbootSession`, 2629 | Restrict SCSI commands, RAM upload/jump ranges, and writable flash sectors; distinguish ROM from the running loader. | `tools/probe_mini_recovery.py:validate_ram_request`, `validate_nor_request`, `MiniRamSession`, and the operational writer's request validator. Keep the MINI-specific payload identities and two-slot lifecycle. |
| `backup_flash`, 4216 | Read all 1 MiB twice, compare, persist the dump and SHA-256, and identify simulated backups separately. The original may read a third time if the first two differ. | `MiniNorSession.read_flash` plus `tools/inspect_mini_backup.py:inspect_backup`. Require two complete equal reads and valid boot/config/application structure; do not treat equality alone as full validation. Retain failed reads rather than silently replacing them. |
| `build_target`, 1623; `plan_sectors`, 1661 | Derive changed sectors from complete before/after images and reject changes outside allowed areas. | The immutable `Installation` in `tools/install_mini_app.py`; retain the exact fresh unit preimage and a MINI-only app range. Existing plan factories need generalization as described below. |
| `_write_plan`, 4314; `UbootSession.write_sector`, 2743 | Verify sectors and final flash; report whether the pedal remains in ROM. | `MiniAppInstallerSession.verify_complete_preimage` and `install_application`, followed by an independent HYRN full read and `tools/inspect_mini_installed.py`. The original invalidation, retry, and rollback policies must not be copied. |
| `check_dump`, 1369; `same_pedal`, 5595; `own_backups`, 5686; `spl_problem`, 5335 | Bind restoration to the device, compatible SPL, backup integrity, and model rather than a filename alone. | `tools/restore_mini_stock.py` provides the explicit app-only restoration model. Its current historical-unit pins must become a new per-unit backup binding. |
| `UbootSession.reboot`, 2775; `wait_cdc_ping`, 4703 | Verify a reset payload in RAM before jumping; confirm application identity after reboot. | `MiniRamSession.start_reset_once`, the MINI reset manifest/ELF, and the independently reviewed boot path. A disappearing USB device or failed jump reply is not boot success. |
| GUI `prepare`, 1715; `show_checklist`, 1810; `start`, 1870; `finish`, 1923 | Show the detected device, chosen operation/backup, progress, and the actual terminal state. | A new small English UI using the MINI state machine; report “verified, still in ROM” separately from “booted and identified.” |

The original `backup_flash`/`_write_plan` implementations are visible at
disassembly lines 28706 and 29190 respectively. `Guard` begins at 17675,
`UbootSession` at 18355, and `RealPedal.send_soft_key` at 20992 in
`recovered/installer/tankg_install.dis.txt`.

## MINI-specific requirements that must replace G/B assumptions

**Target and layout.** Stock entry is supported here for `TANK MINI_009`, not
the original G/B factory-version allowlist. The MINI app range is
`[0x4000,0x82000)`, or `0x7E000` bytes. The UltraRig application range used by
the original G/B installer is `[0x4000,0x7B000)`; its Tank-B stock migration also
handles a different layout. Do not reuse those model tables or VM migrations.
Preserve the MINI SPL/configuration `[0,0x4000)`, VM/OTA `[0x82000,0xBE000)`,
BTIF `[0xBE000,0xBF000)`, USR `[0xBF000,0xFF000)`, and key_mac
`[0xFF000,0x100000)` from the actual unit. The MINI FWSC is not a complete NOR
backup: its `flash.bin` ends at `0x82000`.

**Entry is a state transition, not just a USB ID.** The stock MINI soft key is
`F0 22 24 35 7D F7`; its stock USB-MIDI representation is
`04 F0 22 24 07 35 7D F7`. The `7F` OTA key is a different path. The original
G/B identity parser must not authorize this command on a MINI. The historical
MINI first-install runner demonstrates the stock identify/backup/soft-key
sequence, but its MIDI indices and expected port-name lists belong to one PC.
Bind fresh discovery and identity to the selected physical device instead.
Then require the new ROM enumeration and exact `WL82` / `UBOOT1.00` INQUIRY;
USB descriptor error 43 is not a usable ROM session.

For an already installed HyperRig MINI, use the exact `tankm_fw` PONG and one
`UBOOT\n` request. The firmware's real ACK is `OK UBOOT`; the original installer
can synthesize “OK UBOOT (port closed by the pedal)” after `SerialException`.
Do not reproduce that shortcut. Record the actual ACK, disconnect, native port
closure, and fresh ROM arrival separately. A command requires a responsive
application parser and is not an independent recovery mechanism for a hung app.

**Loader and NOR.** The original `wl82loader.bin`, its `LOADER_ADDR`/argument,
and `hwtest_m13.bin` reset payload are not interchangeable with the MINI
plugins. Use the tested HYRN reader and HYW1 writer in the two 32 KiB slots at
`0x01C20000` and `0x01C28000`. Never overwrite the live callback slot or repeat
an uncertain jump. `MiniAppInstallerSession.initialize_spi` currently requires
JEDEC `0xEB6014`; the read-only reader verifies the 1 MiB capacity. That is a
supported hardware profile, not permission to use another flash revision.
Chip/flash IDs alone do not establish the board layout or boot configuration.

**Ordering and failure handling.** Upstream `_write_plan` first writes an erased
`0x4000` sector, later writes the header last, and can automatically roll back
previous sectors. `write_sector` can also reopen the drive and erase/program
the sector again after a transient error. The MINI implementation intentionally
does not invalidate the header first and does not perform automatic rollback.
Its last sector is `0x4000`; within that sector, pages `0x4100..0x4F00` precede
page `0x4000`. Stage/echo occurs before erase, with page, sector, application,
and independent full-NOR readback. This ordering is not power-loss atomic.

The MINI SPL can enter the staged factory OTA loader when the application
header is invalid. Static analysis does not establish an immediate ROM USB
fallback or automatic stock restoration. See
[the first-boot review](MINI_FIRST_BOOT_REVIEW.md). Preserve the OTA area, but
do not use it as an unqualified recovery guarantee. The footswitch callable
check/reset was tested in RAM; that is distinct from a complete installed
power-on recovery trial and does not cover a damaged guard/header.

**Transport errors.** Reuse `QuietBufferedRomTransport` and its bound
`RomDiskAttestation`, the actual native status/trace logging, and
`BoundedCommandRecoveryTransport` from `tools/recover_mini_read_v6.py`.
Its finite budget does not grant general retries: write reissue requires
the exact pre-execution audit proving non-execution; changed or ambiguous
state stops. `NorReadRecoveryTransport` separately reconciles read counters.
The working Windows path encountered real Win31 failures; changing to a quiet
constructor, buffered I/O, or temporarily pausing media notifications did not
by itself eliminate them. Do not replace the witnessed reconciliation with
an exception-and-retry loop or promise those settings fix the Windows cause.

**CDC opening.** Use DTR true, RTS false, the existing settling period, and the
original bounded five-PING handshake on one open port. Only a fully written
PING with a completely empty timeout can be repeated; partial RX, malformed
responses, and transport errors are terminal. Never infer an unresponsive
firmware from a host opening with DTR false. Exact PONG is a protocol identity,
not a cryptographic attestation of the installed image hash.

## What still needs to become portable

The reusable modules are not yet a turnkey stock-to-HyperRig product:

- `tools/plan_mini_install.py:prepare` requires this unit's historical
  `BACKUP_SHA`; the resume and restoration factories also pin the original
  backup and, in the resume case, the first-install candidate. A new factory
  must accept a verified supported-device profile and a freshly retained
  per-unit full backup, producing a new immutable plan. Do not disable the
  old assertions in place or substitute another unit's dump.
- `tools/build_mini_app_writer_operational.py:checked_inputs` and
  `prepare_installation` validate an operational manifest tied to a particular
  plan and historical qualification. Package the reviewed payload/source
  provenance once, then bind each user's exact plan explicitly. Do not make
  ordinary users reproduce private historical traces or ship those traces,
  presets, identity data, or dumps inside the installer.
- `analysis/hardware/run_mini_final_install.py` starts from a retained reader B
  and a particular interrupted-install dump/counter. It is a proven
  orchestration reference, not the new install entry point. The later
  `run_mini_pc_limit_install.py` demonstrates fresh ROM arrival, reader B →
  writer A → reader B, full before/after comparison, and remaining in ROM
  before a separate boot. Its exact v2→v3 files are also historical inputs.
- `tools/restore_mini_stock.py` restores the stock application only. It
  preserves the current external regions and explicitly does not restore
  historical presets. Upstream `flow_restore` restores app plus USR, while
  `flow_factory` can use a packaged factory USR image; neither is an authorized
  MINI default. Full data restoration would need a separate reviewed design.
- The available transport is Windows-specific. “Portable installer” can mean
  a self-contained Windows folder without a preinstalled Python environment;
  it does not establish Linux/macOS support. The original PyInstaller archive
  layout is useful packaging evidence, but `hyperrig/branding.py` and
  `tools/rebrand.py` rename G/B packages without implementing MINI support.

## Recommended implementation sequence

1. Verify the package's MINI v3 app, writer/reader/reset payloads, metadata,
   licenses, and backup destination before entering a device mode. The current
   installed v3 app SHA-256 is
   `9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c`.
   Keep firmware qualification separate from the English editor's presentation
   bundle.
2. Detect one supported stock MINI, identify it freshly, and export its stock
   preset bank with `ReadOnlyMini.backup`. That small export is not the required
   full NOR recovery backup. Send the stock soft key once, then prove fresh ROM
   arrival and INQUIRY before uploading the reader.
3. Acquire and durably retain two full 1 MiB reads. Validate their equality,
   stock boot/config/application CRCs, known MINI layout, actual NOR identity,
   and unit-specific tail. Build the new unit's immutable app-only plan.
4. Upload/verify/start the writer in the inactive slot; verify the whole fresh
   app preimage again. Execute the bounded header-last plan with durable intent
   logging and the existing witnessed recovery policy. On unresolved failure,
   stop in ROM and offer a fresh read plus explicit resume/restoration plan.
5. Start the reader in the now-inactive slot, acquire another complete NOR
   image, and independently compare the app to the candidate and every external
   byte to the fresh preimage. Only then offer the separate one-shot reset and
   normal boot/identity check. Preserve the distinction between installed,
   booted, connected, audio tested, and recovery tested.
6. Close the native installer port before opening the current HyperRig editor.
   Show the backup path and result; offer local logs and
   [HyperRig GitHub issues](https://github.com/danmigdev/hyperrig/issues/new/choose).
   Do not carry over upstream donation/community buttons, default-enabled
   `end_report_box`, `finish_install_note`, `send_run_report`, or automatic
   uploads. Keep the interface English and require no system service.

The original GUI's detection/operation/progress/result structure is useful;
its command routing and backend must be rebuilt around these MINI contracts.
Existing `tools/mini_admin_session.py` demonstrates a temporary elevated worker
with pinned jobs and no automatic replay. A packaged UI can adopt that separation
without exposing a shell or requiring a new elevation for every transfer.
