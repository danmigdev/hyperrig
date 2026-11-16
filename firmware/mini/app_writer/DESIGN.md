# MINI application writer: implementation with target mutations disabled

This directory contains the HYW1 protocol, separate PIO driver, and writer
core. The initial target has a **constant zero mutation gate**: FC7B and
FC7D cannot reach WREN through dispatch. The already tested HYRN reader
remains unchanged. Host tests enable mutations only on in-memory NOR;
the same macro is forbidden when compiling the target.

Command `python tools/build_mini_app_writer.py --build-locked` builds two
RAM payloads of at most 32 KiB, runs tests, and verifies the zero gate in the
ELFs. The default CLI checks only the local plan. No hardware writer client,
force option, or enabled target mode exists. The plan is rechecked against
the candidate, full backup, and rollback before the report; hashes for all
126 sectors and CRCs for the 2,016 pages are included.

## ROM evidence and the remaining explicit limitation

The pinned source is `upstream/m-bootloader`, commit
`3ac7651a019fa44daba061b05654278496477b64`. In `src/loader_target.c:19`,
`params[1]` is interpreted as `int receive(void *, uint32_t)`.
In `src/loader.c:14`, the loader calls the callback with chunks no larger
than 512 bytes, ignores its return value, and advances the pointer regardless.
This establishes the signature and convention used by the loader; it does
not establish a complete receive.

`docs/SPEC.md:835` explicitly states that return values and partial/error
transfer semantics are unknown. Available code does not resolve this general
gap. Assuming `return >= 0`, `return == 0`, or `return == length` means
success would be a choice unsupported by evidence. A correct CRC checks the
observed bytes; it is not general proof of callback semantics or completion
of an asynchronous transfer.

HYRX subsequently observed one 260-byte OUT on MINI, raw return 260,
exact data, and two stable records with intact canaries.
Captured records and the executed manifest are pinned in the writer report.
Observed callbacks are send `0x01E008E4`, receive `0x01E0089A`, and handler
slot `0x01C01264`: this target's entry rejects different values before SPI.
The test does not qualify errors, general buffer lifetime, or synchrony.

To reduce this dependency, the writer receives into a guarded arena, requires
the observed return 260, and copies the page into a **second frozen buffer**.
It verifies the copy's CRC, exposes exactly those 256 bytes through FD87,
and requires a separate FC7D command after echo. The host must compare every
byte before FC7D. PP uses only the frozen copy: late writes to the preceding
RX buffer do not change the programmed source. Copy guards and CRC are
rechecked before WREN; any inconsistency is rejected.

## Future writer limits

The sole allowed physical range is `[0x4000,0x82000)`: 126 sectors of
4096 bytes, each with 16 pages of 256 bytes. A check must precede any 24-bit
command calculation: `address >= start`, `address < end`, positive length,
and `length <= end-address`. Addition overflow, unaligned sectors, pages
outside the sector, and CPU/XIP addresses must also be rejected.

SPL/initial configuration, all VM including OTA/request, BTIF, USR, and
key_mac remain excluded. The rollback plan must refer to this unit's full
backup, not a generic FWSC. Header-sector-last ordering does not make
installation atomic or replace independent recovery.

Before the first destructive access, exact JEDEC `EB6014`, capacity
1 MiB, consistent WIP/WEL status, and no protection are required.
SPEC §3.4 documents SR1 `0x7C` and SR2 `0x40` for this family:
the writer must **reject**, not clear, active protection.
It must not write SR1/SR2, change QE, or attempt an unlock sequence.
Volatile PIO configuration must derive from the MINI reader; its initialisation
must not be replaced by generic upstream initialisation, which changes clocks
and may change NOR status registers.

## Proposed HYW1 sequence

Opcodes and fields are described exactly in `protocol-draft.json`.
Every CDB is 16 bytes, with BE integers and unused padding `FF`;
the CBW must declare exact direction and length. Tokens are single-use
counters, not authentication. An error invalidates mutation authorisation;
there is no automatic retry, implicit resume, or command to clear the error.

1. Entry/FC78 register and identify the plugin without MMIO. FC79 is explicit
   initialisation, with JEDEC/status reads and no WREN.
2. The host reads the sector and checks SHA256 against the plan.
   FC7A rereads all 4096 bytes and compares preimage CRC32 before arming
   only that sector. CRC32 does not replace the host's SHA256 comparison.
3. Before any WREN, including erase WREN, a first page must already have
   been received, frozen, and exposed through FD87 for host comparison.
   In the operational path tested on the mock, FC7B consumes token/sequence,
   rechecks preimage/status, WREN, and WEL, then performs one erase20.
   WIP has a finite bound, and every sector byte must read FF.
   Actual timing limits still need qualification.
4. FB7C receives a full page plus CRC into RAM; **it does not write flash**.
   It is also allowed before erase, to verify staging/echo on the locked
   target. FC7E must confirm staging, and the host must compare FD87
   byte-for-byte before FC7D. Only FC7D may consume the page, recheck CRC
   and that the page remains erased, verify WREN/WEL, and program one PP02
   without crossing a 256-byte boundary.
5. After each mutation: bounded WIP, checked WEL/status, CS high even on
   error, a full read, and byte comparison. A PP error may have already
   programmed part of the page: no automatic rollback is claimed, and PP
   is not repeated to hide a transport error.
6. FC80 verifies the 16-page bitmap and full-sector CRC. The host rereads
   the sector and compares SHA256, then the entire application area.
   The next sector requires a new token. Sequence restarts at 1 only
   under that new token; FD87 uses the staging sequence, retained even
   when a later erase advances the current sequence.

The initial target rejects erase/program before any destructive operation.
STAGE/echo after ARM remain real RAM operations, without simulating erase.

The OUT response includes no extra IN packet: its result is read separately.
A failed host response after a destructive command means an ambiguous outcome,
not permission to retry. ROM FB06/FD07/FB08 remain part of RAM lifecycle;
the writer client must not expose them generically. Rejected legacy commands
must not fall through to ROM's flash handler.

## Record and stack

FD88 returns 128 LE bytes of already collected state, without rereading NOR.
The record contains HYW1 magic, version, base/tag, phase/error, token/sequence,
sector/page, preimage/target/page/last-read CRCs, JEDEC, SR1/SR2,
WREN/erase/PP/read/poll counters, receive return, guards, page bitmap,
staged/echoed, and stack guards/observed usage. Zero gate at 116, CRC32 of
the first 120 bytes at 120, and DONE at 124. FC7E does not clear sticky errors.

NOR work uses the guarded 4 KiB private stack through the already verified
pi32v2 bridge. USB callbacks remain on the original ROM stack.
ELFs must have a single RAM segment in the slot, entry at the first byte,
no unresolved symbols, and no overlap among code, state, record, and stack.
Automatic audit also checks exact bridge bytes and the zero gate.
ROM interrupt-stack availability remains outside this static test;
hardware execution of the writer is not claimed.

## Completed and remaining checks

C tests with ASan/UBSan cover complete installation of a sector at both ends
of the area, SR1/SR2 protection, absent/persistent WEL, stuck WIP, wrong CRC,
all 260 short-receive lengths, corrupted guards, duplicate tokens/sequences,
4000/81F00/82000 bounds, partial PP, wrong readback, and frozen-buffer isolation.
A separate SPI model injects timeouts at each of the 544 bytes in the
init/status/WREN/erase/program/read sequence: CS is always released, and
a failed transaction is not retried. The zero-gate test checks staging/echo
and erase rejection without WREN.

The PIO bound is 32,768 polls per byte; WIP allows at most 65,536 samples,
with 256 wait iterations between busy samples. These are finite bounds,
not certified timing measurements. Compatibility with host timeouts and
physical erase/program times requires review before the enabled build.

Root manages the current gates: the user's chosen footswitch recovery,
codec/board and exact candidate, then review of the enabled build.
No USB_KEY prerequisites, GPIO wiring, or new project approvals are added.
The builder does not promote hardware readiness or execute commands on MINI.
