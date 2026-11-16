# ROM recovery and first RAM code on TANK MINI

Official `TANK MINI_009` firmware contains a USB MIDI command to request
ROM download mode. The command was reconstructed from MINI bytes;
m-flasher's MIDI allowlist does not include this model.
`tools/probe_mini_recovery.py` produces offline evidence and vectors and
provides an explicit Windows API for transfers restricted to RAM and NOR reads.
Importing the module or running its CLI opens no device.

Client tests use in-memory transports and substituted Windows APIs.
Physical results are recorded separately in `analysis/hardware/`:
`research/mini-recovery.json` describes offline verification; it does not
certify hardware boot or recovery after corrupted flash.

The subsequent physical test of 15 November 2026 is recorded in
[mini-hardware-rom.json](../research/mini-hardware-rom.json). USB entry into
ROM, DSP-probe execution, NOR-reader startup, and reset to stock succeeded.
Return was verified by a new `4C4A:C755` enumeration, a `TANK MINI_009`
response, and two preset reads identical to the preceding backup.
After a first partial acquisition interrupted by a USB error and a hub reset,
two identical full 1 MiB reads with valid stock 009 content succeeded.
Recovery from corrupted flash and NVM restoration remain to be tested.

## MINI command and path verified in stock bytes

The reference container is `artifacts/tank-mini/TANK-MINI.fwsc`, SHA256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
A different container is rejected before analysis.

| Object | Value |
| --- | --- |
| SysEx | `F0 22 24 35 7D F7` |
| Two USB MIDI packets, cable 0 | `04 F0 22 24 07 35 7D F7` |
| Stock pattern in RAM | `0x01C0AFC4` |
| Command guard | `0x0200869A..0x020086DE` |
| Download-request routine | `0x01C02332..0x01C02382` |
| Preserved string | `usb_update_mode\0`, 16 bytes |
| String source/destination | `0x0203FD2A` / `0x01C7FD80` |

The guard requires eight bytes, compares the first six against the pattern,
and separately checks the final `F7` and command `7D`. The model executes
the decoded instruction flow up to the recovery call: one positive case and
73 negative variants, including every single-bit change, truncated lengths,
and an extra byte. `memcmp` was inspected separately.

The following routine disables interrupts, serialises access, copies the
marker, and calls P33 helper `0x01C0108C` with arguments `(0xA0,4,1,1)`,
then waits. The offline model performs neither that write nor a reset.

USB registration `0x02007ED0` installs callback `0x02008864`, which reads
USB data and passes it to `0x02008784`, then to the guard. No equivalent
BLE path into this callback has been proven. Being able to read BLE presets
does not establish that the USB-mode command can be forwarded there.

## ROM protocol and data transformation

AC791N sources describe two RAM slots, `0x01C20000` and `0x01C28000`,
each `0x8000` bytes. A slot must be known free or contain an upload never
executed, with complete history. INQUIRY alone does not prove a slot is free.

Each private CDB is 16 bytes long, padded with `FF`:

| Operation | CDB and data phase |
| --- | --- |
| ROM upload | `FB06`, BE32 address at +2, BE16 length at +6, zero at +8, LE CRC16 at +9; OUT maximum 512 bytes |
| ROM read | `FD07`, BE32 address at +2, BE16 length at +6; IN maximum 512 bytes in the client |
| RAM call | `FB08`, BE32 entry at +2, BE16 parameter `1` at +6; IN 16 bytes |
| HyperRig identity/selftest | `FC60`; IN 16 bytes |
| HyperRig plugin read | `FD61`, BE32 address and BE16 length; IN maximum 4096 bytes per command, callback in 512-byte chunks |

`FB06` transmits data transformed with `jl_crc_cipher`, key `FFFFFFFF`.
State restarts for each command. The CDB's CRC16/XMODEM uses a zero seed
and covers the **transmitted**, already transformed bytes. The transformation
is symmetric and separate from flash ENC/SFC encryption.

**`FD07` also returns transformed data.** The client decodes each response
separately, verifies its length, and compares the entire image with the
approved SHA256 file. It does not automatically try other encodings or accept
a partial match.

This distinction is documented in the original installer disassembly:
`UbootSession.reboot`, original lines 2786 and 2791, applies
`enc(mem_read(...))` before checking the sentinel and image.
`enc` uses `cipher_bytes(jl_crc_cipher,
b)`, with default key `FFFFFFFF`; `JL_LoaderV2.mem_read` returns the raw
response.

In the first MINI attempt on 15 November 2026, the earlier client incorrectly
compared the raw response with the file and stopped without issuing `FB08`.
Offline analysis of `analysis/hardware/rom-probe-trace.jsonl` found all ten
received hashes equal to the expected transformed blocks (nine 512-byte blocks
and one of 320), none equal to plaintext. The correction retains full
verification before jumping. A session with history proving zero `FB08`
commands can reread the upload already present; it need not overwrite it.

`FD61` belongs to the uploaded plugin. m-flasher `run-ram --read` uses
`FD61`; this does not prove that ROM directly implements that command.
After an `FB08` with a lost response, code may already have executed:
the client marks the session before the call and never repeats the jump.

## RAM plugin contract

Entry is the first byte of the flat file. ROM calls it as a C function:
`r0` points to three words containing the send callback, receive callback,
and address of the ROM variable holding the protocol callback.

The plugin preserves these values, initialises only its own state, publishes
its handler with synchronisation, and returns normally. The contract preserves
the ROM stack, clocks, interrupts, USB service, and other slots' RAM.
It neither uses MINI application startup nor clears all RAM.

The handler receives `CBW31 *` in `r0` and a 16-byte response buffer in
`r1`; it returns one for a handled command and zero to delegate to ROM.
The CBW contains LE signature `0x43425355`, tag at +4, LE count at +8,
direction at +12, CDB length at +14, and CDB at +15. The plugin sends data
through the supplied callback; ROM produces the CSW. The exact semantics
of callback return values cannot be fully deduced from sources; the client
still checks the data phase, identity, and contents.

The HYR1 probe is built by `tools/build_mini_rom_probe.py`. `FC60`
responses contain a BE32 count at +2, `HYR1` at +6, BE32 status at +10,
and BE16 version at +14. The client requires zero status, version one,
and a positive count. The probe manifest defines the eight cases and expected
CRCs; a positive result is not equivalent to execution of the entire A2 engine
or audio path.

## Windows client and slot sequence

`WindowsRomTransport` requires 64-bit Windows Python and an explicit
`\\.\PhysicalDriveN` path. Before opening, it checks the PnP chain for
ancestor `USB\VID_4C4A&PID_8057`; after opening, it requires INQUIRY
`WL82` / `UBOOT1.00`. A device with descriptor error 43 does not meet
these conditions.

Transfers use `SCSI_PASS_THROUGH_DIRECT`, IOCTL `0x4D014`, target 1,
a 10-second timeout, and a 32-byte sense buffer. On 64-bit Windows, the
SPTD structure is 56 bytes; the buffer including sense is 88 bytes.
The Windows driver constructs USB BOT framing: the client does not manually
add a CBW. Opening requires protocol READ/WRITE rights on the device handle;
CDBs remain restricted by the allowlist. The module has no automatic elevation,
mode change, or retry.

If `DeviceIoControl` fails, `RomCommandError` immediately preserves the
Win32 code and includes SCSI status, transfer length, bytes returned by the
IOCTL, and sense buffer in `details`. It does not include the NOR data buffer.
These fields may be incomplete when the IOCTL fails and are not interpreted
as evidence of a successful transfer. To measure duration, the caller must
record an end time separate from the start time.

| API | Condition and effect |
| --- | --- |
| `upload_only` | Slot known free, manifest hash verified; `FB06` only |
| `verify_upload_only` | Upload known never to have executed; `FD07` only, decoding and full comparison |
| `verify_and_start` | Repeats full verification, issues one `FB08`, verifies HYR1/HYRN |
| `upload_and_start` | Combines upload, verification, and execution |
| `read` | Only after HYR1; exposes only the plugin's slot |
| `start_reset_once` | Verifies manifest, ELF, and a fresh RAM read; one jump without HYR1 handshake |

`known_free_slot=True` and `known_uploaded_unstarted=True` are explicit,
mutually exclusive declarations based on caller history. Creating a new Python
object does not free the physical slot. After a plugin in slot B has published
and confirmed its handler, the old plugin's slot A can be reused, provided
no other pointers or activity toward it remain. If the jump to B has an
ambiguous outcome, the active handler is not inferred and neither slot
is overwritten.

## Separate NOR reading, without nonvolatile writes

The `nor-reader` profile uses the source reader in
`firmware/mini/recovery_reader/`, manifest `research/mini-flash-reader.json`.
Loading registers the HYRN protocol without initialising SPI.
`MiniNorSession.initialize_spi()` is a subsequent explicit phase.

| HYRN command | Response/action |
| --- | --- |
| `FC70` | Identity `HYRN`, version 1, flags 3, slot base and span; no MMIO |
| `FC72` | PIO setup, exit from continuous-read, JEDEC; status, capacity, and divisor |
| `FD71` | Physical read of 1..512 bytes within verified capacity |
| `FC73` | Sticky error, initialisation, clock snapshot, and read-byte counter |

The reader issues SPI commands `FF FF`, `9F`, and `03`. It contains no
write-enable, program, erase, or status-write commands. Setup changes volatile
SFC/SPI/pinmux registers while keeping code and data in RAM. Capacity must
be exactly 1 MiB from JEDEC, not from the FWSC package size.

Every `FD71` must be followed by `FC73`. A sticky error, unexpected counter,
or short transfer invalidates the block and session. This prevents confusing
the reader's error-fill `FF` with valid flash data. Subsequent reads in the
same session retain the cumulative counter, including between two complete
passes.

A full backup requires two physical reads from `0x000000` to `0x100000`,
valid status for every block, exact lengths, and byte-for-byte/hash comparison.
Neither a RAM-slot read, the CPU SFC window, nor the stock FWSC file constitutes
such a backup. A full copy alone does not prove recovery from corrupted flash:
the application-independent ROM path and restoration procedure still require
verification.

The AC791N SPEC also describes the physical `USB_KEY` dongle as mask-ROM
entry independent of the bootloader. The source concerns FM-1/SMK-37; it does
not prove operation on MINI. No MINI footswitch combination has been established
as a substitute for this path when the application fails to start.

## Controlled RAM reset

Reset is a separate artifact (`research/mini-rom-reset.json`), without the
HYR1 protocol. `start_reset_once` requires the artifact manifest, ELF bytes,
and flat bytes; it verifies digests, entry, the single pi32v2 segment inside
the slot, and the absence of BSS/relocations. The manifest must come from the
already reviewed reset build: the client parser proves the file/layout
relationship, not the semantics of arbitrary code.

The reviewed reset invalidates the first word of marker `0x01C7FD80`, sets
bit 4 of `0x10000`, and waits. After a new full `FD07` verification, the
client issues only one `FB08`. A disconnect following the IOCTL call is
recorded as an ambiguous outcome; it is not converted to success.
Validation, read, or transport errors before submission remain exceptions.
The new normal USB identity `4C4A:C755` must be observed separately and
`TANK MINI_009` identified.

## Offline reproduction and sources

```powershell
python -X utf8 tools/probe_mini_recovery.py
python -X utf8 -m unittest tests.test_mini_recovery -v
```

The 20 tests check the MINI guard, an independent bitwise CRC model,
endianness/CDB, upload and readback in both slots, no execution after mismatch,
no retry after an ambiguous jump, resume with a fresh read, NOR profile,
per-block status, manifest/reset, and a fully simulated Windows layout,
including preservation of failed-IOCTL details.
They do not electrically model USB, flash, or reset.

Pinned primary sources:

- [m-bootloader SPEC, commit 3ac7651](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md), sections 6.3 and 10.1; local copy `upstream/m-bootloader/`.
- [pi32v2 hwtest runner, commit 1f09804](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/tools/hwtest/runner.S).
- [m-flasher, commit 8fbece7](https://github.com/jvitkauskas/m-flasher/tree/8fbece7348d758ac284325eed455781675ac95ff), `src/jl.rs`, `usb.rs`, `scsi.rs`, `midi.rs`; source hashes in the report.
- MINI firmware and original-installer disassembly in `recovered/installer/`; no FM1/SMK37 installer or loader was executed for this analysis.

Official `ota.bin` is a JLFS container with `usb_hid_ota.bin`, 19958 bytes
in total, SHA256 `9c62bbdfd55f6527a3cffe43abc16c621d0900a8ff47685240abb1ee596eb66e`.
Its path is an update with flash staging; it is not the flat plugin with ROM
callbacks and is not used for this RAM test.
