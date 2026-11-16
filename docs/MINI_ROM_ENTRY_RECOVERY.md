# HYK1: testing footswitch recovery in RAM

HYK1 separately qualifies the frozen `entry_recovery/check.S` and `reset.S`
functions. It is a ROM diagnostic plugin in the two slots already used by the
project; it contains no G application prefix, changes no clocks or flash, and
does not set application stacks. On 15 November 2026, the three-switch checks
and subsequent explicit reset to ROM were verified on the MINI. The
[mini-entry-recovery-hardware.json](../research/mini-entry-recovery-hardware.json)
report keeps physical evidence separate from the build manifest. The guard
during application startup and state at cold handover remain unproven.

In the checkout with pinned dependencies, the offline build commands are:

```powershell
python -X utf8 tools/build_mini_rom_entry_recovery.py
python -X utf8 tools/probe_mini_entry_recovery.py
```

The first command compiles and tests; the second only displays the protocol,
without searching for or opening devices. The manifest that can be frozen is
`research/mini-rom-entry-recovery.json`: it includes the build tag, hashes of
all dependencies, and both `build/mini-rom-entry-recovery/*.bin` files. The
shared transport is bound to SHA256
`1d512173776f5f87424e7870731df2871cdf1f9293636765a6371c7bb44191e8`.
The test manifest remains unchanged, including the false hardware flags that
attest to the builder's offline work. Future dispatcher revisions do not change
this historical pin: the copy used for verification is archived in
`analysis/hardware/recovery-dispatcher-1d512173.py` with the same hash.
Sealing results neither recompiles nor regenerates the executed artifacts.

## Explicit operations

Every private CDB is 16 bytes with `FF` padding, IN direction, and LUN 0.
Integers in CDB arguments are big endian. The ROM infrastructure additionally
uses only INQUIRY and the already verified RAM opcodes FB06/FD07/FB08.

| CDB | Arguments after opcode | Response | Effect |
| --- | --- | --- | --- |
| FC74 | none | 16 bytes, `HYK1`, version 1, slot | Identity; no peripheral reads |
| FC75 | none | 16 bytes + record through FD77 | Two passive PORTA and clock snapshots |
| FC76 | snapshot sequence + record CRC32 | 16 bytes + new record | One explicit PA10/PA0/PA3 check per valid snapshot |
| FD77 | current sequence | 256-byte record | Exposes the current record |
| FC81 | sequence + CRC32 + `ROM!` | no response promised | Explicit marker/reset request, once only |

Sequence and CRC prevent accidental reuse of an earlier snapshot; `ROM!`
distinguishes the command that destroys the session. **They are not
authentication.** FC76 does not send FC81, even when it detects all switches
held. No error triggers an automatic reset.

The record, described in `rom_entry_recovery.h`, includes build tag and sequence,
check result, snapshots of nine PORTA registers and twelve clock words,
restored-register verification, stack guards, CRC32, and the `DONE` terminator.
The parser also checks internal consistency of flags and results; a valid CRC
alone is insufficient. IN-register changes are allowed: footswitches can move
during a read. The other eight PORTA registers must remain identical, including
bits outside the three affected inputs.

Callable results are 0 (combination not maintained), 1 (three inputs low for
all samples), and 2 (initial direction or configuration rejected). Diagnostic
statuses are -3 for result 2, -6 for changed GPIO configuration, -7 for stack
guards, -8 for changed clocks, -9 for an unexpected return from the reset
callback, and -10 for an unknown callable result.

## Client integration

`MiniEntryRecoverySession` reuses `MiniRamSession` and the Windows
`ram-entry-recovery` profile. The caller supplies the transport, slot, and
build tag read from the verified manifest. The runner-authorized procedure is:

1. Establish that the slot is free through ROM-session history. INQUIRY alone
   does not prove that no plugin is using the slot.
2. Call `upload_only(image, expected_sha256=...)`, then `verify_and_start(...)`.
   The latter compares decoded FD07 before the single FB08 and requires FC74
   identity. It does not take snapshots or check switches.
3. Call `snapshot()`; only a valid snapshot with all three pins already inputs
   enables `check()`. Each `check()` consumes the snapshot before I/O, even if
   the response is lost. A new check requires `snapshot()`.
4. Save records and results. A check with released switches and one with all
   three held distinguish the two physical conditions.
5. Only for the explicit return-to-ROM test, capture the preceding USB arrival
   and call `request_rom_reset_once()`. This makes the session terminal
   **before** I/O. Do not retry FC81.

`request_rom_reset_once()` never declares reset completion: even a valid USB
response could belong to the previous ROM session. The runner must observe a
new USB enumeration with a later `DEVPKEY_Device_LastArrivalDate`, followed by
a new `WL82 / UBOOT1.00` INQUIRY. Any hub restart must be recorded separately:
it does not prove that FC81 caused a CPU reset. A transport error after sending
is ambiguous and does not authorize a second send. The runner preserves logs
and independently manages the subsequent return to firmware.

## Code and qualified limits

Both ELFs fit entirely within their respective 32 KiB slots, `0x01C20000` or
`0x01C28000`. The record and all variables belong to the slot. The private
stack is 4096 bytes, with 32 guard bytes on each side. The trampoline preserves
the ROM stack and RETS; transmission callbacks are called after returning to
the ROM stack. The linked-code call audit derives a maximum of 60 bytes on the
private stack, excluding any inherited ROM interrupt stack. It does not
explicitly write SSP, ICFG, IRQ, PLL, or SFC; the active SP register is restored
by the trampoline.

The callable sets input/digital/pull-up only on PA10/PA0/PA3, rejects before
writing if it finds a pin configured as output, then restores the selected
configuration. Delays are counted instruction loops, without conversion to
milliseconds: ROM clocks and actual command duration remain to be measured.
Reset writes `usb_update_mode\0` to `0x01C7FD80`, executes `csync`, sets bit 4
of `RST_CON` at `0x00010000` through RMW, executes `csync`, and waits. If reset
is not delivered, it remains waiting; there is no arbitrary jump into ROM.

The checks are distinct:

- 909 C dispatcher cases executed on the host under ASan/UBSan with simulated
  callbacks;
- 11 client tests on a simulated transport, including upload/readback/jump,
  response loss, token consumption, and prevention of reset retries;
- 99 cases per slot on a model of the actually linked `check.S` and `reset.S`
  instructions, plus trampoline and ELF-bound checks;
- rejection of malformed records and out-of-contract ELFs.

Host tests use synthetic observed-stack values only in parser fixtures. They
are not measurements of hardware stack usage, GPIO, or reset.

## Physical test on 15 November 2026

HYK1 ran in slot A `0x01C20000`: a 2,472-byte payload and 6,944 bytes of private
RAM, including stack and guards. The build tag is `2348256965`; the application
prefix is absent from the ELF.

| Test artifact | SHA256 |
|---|---|
| Manifest | `eb6673b00dab2a8e0ca2141313b95a6441fb7bf882bb4a4e2076c99dfdd23516` |
| HYK1 A payload | `02a875e24470c7168a74be3a89ee10be3cf324fb3ebe954302fb64332e48a88b` |
| HYK1 A ELF | `49977d1e7b84c5c20a62e3a6737f87f8e1e1a5a62976a432957f4251578ee3e9` |

Three consecutive check sessions produced six records: each snapshot was
followed by a single `check`. The preceding record is reread before resuming
the session; the chain of four journals preserves the previous phase's hashes.

| Condition | Check sequence | PORTA.IN | IN & `0x409` | Result |
|---|---:|---:|---:|---:|
| Switches released, baseline | 2 | `0x7FF` | `0x409` | 0 |
| All three held | 4 | `0x3F6` | `0` | 1 |
| Switches released again | 6 | `0x7FF` | `0x409` | 0 |

This qualifies the active-low PA10/PA0/PA3 group in the test's ROM context.
It does not individually assign physical labels A/B/C to the three pins. All
six records preserve the eight GPIO configuration registers, twelve clock
words, and stack guards. Observed private stack usage is 60 bytes, equal to
the limit derived from linked code; ROM interrupt-stack capacity remains excluded.

The hashes of the three check records are:

- baseline: `71a8daf5112d06d5a8012822345b0ec765916902a7b43372088f81d5024bd530`;
- held: `a3e10f0e0fb7f3b141a8c4249fb9866589fc782a317807c48ba3a4a28bc8335b`;
- released: `579849e0fec99e15ba565640ba64d76a4bb57d35b6553de2f2d89141949c6408`.

The report also includes the three snapshots and all complete records, with
CRCs, sequences, and hashes. They were rechecked offline with the frozen
validator, together with 26 pinned files, the ELF, decoded FD07, nine record
reads in the trace, and 34 command/outcome pairs. The 909 C cases, 11 client
tests, 99 instruction cases per slot, and negative checks remain results
already attested by the manifest; they were not recompiled for this account.

Reset was an **explicit FC81 request** after the released-switch check, not an
automatic consequence of pressing the switches. The single command, bound to
sequence 6 and its record CRC, was sent at `19:59:11.814222Z`. It produced
transport error 121, so its response is not evidence of completion. The evidence
is the new enumeration of the same USB instance, whose arrival changed from
`19:54:53.5112400Z` to `19:59:12.5150710Z`, followed by a new
`WL82 / UBOOT1.00` INQUIRY. The hub was not restarted and FC81 was not repeated.
No mailbox read was performed after reset.

From the new ROM session, the separate stock reset was uploaded, read back,
and started once in slot B: 26 bytes, SHA256
`cf3526d914eef007649f88f1f22e085a908359b9ad0e9f4743427b4757c0540f`.
The jump also produced a transport error; the actual return is attested by
the subsequent `TANK MINI_009` identity and unchanged presets: two identical
reads, 1,942 bytes, SHA256
`c6216783618016998488515ecf4272a78ace8e82ca22e3a27a42bc2d76100427`.
The journal ends in phase `complete` at `19:59:37.747148Z`. This is the seventh
verified return to stock, in this case without a hub restart. No NOR write or
clock change was performed.

These results qualify the switch callable and marker/reset path from ROM.
They do not qualify the application prefix, a cold boot from flash, or recovery
from a corrupted application; those gates remain closed.

## SPL handover and future application prefix

No supported, verified path was found in the analyzed interfaces to observe
the exact GPIO state at **cold SPL → application** handover using RAM alone.
USB ROM precedes a different path; the stock application's USB functions run
after peripheral initialization. SPL point `call r1` at `0x01C0528C` uses the
entry read from flash; no RAM observation hook has been identified there.

Manually executing an SPL copy from ROM would first require qualification of
the ABI, RAM ownership beyond the two slots, SFC/cache, and USB shutdown; it
still would not equal a cold boot. The OTA path has a distinct ABI and does not
itself provide that observation. These are limits of the available evidence,
not proof that no other method can exist.

A future revision of the **application prefix**, separate from this probe,
can save context and then permanently set `PORTA.DIR |= 0x409` before calling
the frozen callable. In the complete port, those three pins are footswitches
and subsequent initialization requires them to be inputs: the callable will
therefore save and restore an already-input direction, without re-enabling an
output against a pressed switch. This policy removes dependence on the unknown
initial direction at cold handover; it does not require pretending that ROM
state equals SPL state. The ROM probe instead retains output rejection and
full restoration. This build neither implements nor links the prefix.

The future entry guard can recover a valid image that hangs after executing
it. Damage to the header, entry, or guard itself remains a different case;
the HYK1 test does not demonstrate universal recovery of every corrupted app.
