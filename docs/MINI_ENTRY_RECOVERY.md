# Footswitch recovery at G application entry

A small guard can be inserted before the first call in UltraRig G firmware.
The component in
[`firmware/mini/entry_recovery`](../firmware/mini/entry_recovery) occupies
**282 bytes of code**, with no BSS, data to copy, heap, or dependencies on the
RTOS, GPIO helpers, G clocks, or DSP. It is assembled and verified offline;
**it is not included in the candidate and has not run on the MINI**.

The chosen combination is **all three footswitches held before power-on**.
It requires no assignment of physical A/B/C labels to pins, which is still
unconfirmed, and distinguishes recovery from two-button operating combinations.
If the combination is detected, the guard writes the ROM mailbox and requests
the documented reset. Otherwise, it preserves context and continues original
startup.

This can recover a valid application that hangs **after** the guard: power the
pedal off and on while holding the combination. It requires neither USB
processing by the hung firmware nor an armed watchdog. A USB bus reset alone
does not restart the pedal CPU.

## Insertion point and ABI

| Original G point | Byte evidence |
|---|---|
| `0x02000120` | Short jump to `0x0200018A` |
| `0x0200018A` | `sp = 0x01C350B8`, six bytes |
| `0x02000190` | `ssp = 0x01C360B8`, six bytes |
| `0x02000196` | First call, to `0x0200042E` |

The twelve-byte preimage is:
`eeffb850c301edffb860c301`.
The proposal replaces only these twelve bytes with a jump to the prefix and
four NOPs. It preserves the entry, vectors, and instructions near
`0x02000120`, avoiding overwriting them to make room for a long jump.
The existing formatter has not changed.

The prefix repeats the two original stack setups exactly, saves the sixteen
general registers, PSR, RETS, and RETI, calls the check, and, when continuing,
restores them before jumping to `0x02000196`. In particular, **r0 is restored
unchanged** and continues to point to the bootloader context. Copies of absent
boot extensions remain handled by the existing separate patch.

The maximum added frame is 100 bytes: 76 for the prefix and 24 for the check.
Both interpretations of SP already discussed in
[MINI_ROM_STACK.md](MINI_ROM_STACK.md) are considered: a range below
`0x01C350B8`, or below `0x01C360B8` if SP aliases the supervisor stack.
Both remain in G application RAM, away from the mailbox. The model does not
determine the active physical mode; it reproduces the original setups under
both interpretations.

Interrupt policy and CPU mode are unchanged. The original SPL executes `cli`
at `0x01C051C2` before handover `call r1` at `0x01C0528C`. The prefix assumes
this SPL entry; it does not support an arbitrary jump from a task or IRQ.
G GPIO helpers cannot be used here: their locks and runtime data are not yet
initialised.

## GPIO and possible false detection

MINI firmware configures PA10, PA0, and PA3 at `0x02006096..60BA`; the read at
`0x0200A060` uses PORTA IN (`0x50004`). The active-low interpretation is
reconstructed in the [panel audit](MINI_PANEL_PORT.md). The register layout is
corroborated by the [pinned WL82 SDK header](../upstream/ac79-sdk-reference/include_lib/driver/cpu/wl82/asm/WL82.h).

The check owns only mask `0x409`:

| Register | Address | Temporary operation |
|---|---:|---|
| DIR | `0x50008` | Input |
| DIE | `0x5000C` | Digital input enabled |
| PU | `0x50010` | Pull-up enabled |
| PD | `0x50014` | Pull-down disabled |

Before writing, it verifies that all three DIR bits already specify inputs.
Otherwise, it returns an error without writing GPIO. This avoids a later
restoration turning a pressed button into a driven output. OUT, DIEH, drive
strength, and mux are not written. Changes use read-modify-write; on return,
only the three owned bits are restored, preserving the current unrelated bits.
No other executor may change these pins during the check.

The code checks configuration readback, waits 100000 iterations, and requires
32 samples with all three bits low, separated by another 100000 iterations.
The first sample with any bit high continues startup. These are software
counters, **not measured milliseconds**; they establish neither a physical
debounce time nor continuity of the level between samples. No REP, timer,
or PLL changes are used.

The callable function returns 0 (combination absent), 1 (combination observed),
or 2 (invalid initial direction or readback). The prefix requires exactly 1
to reset. Result 2 continues G: this avoids accidental recovery due to a
configuration error, but means **the guard cannot be relied on in that state**.

A permanently zero GPIO read may be indistinguishable from three pressed
buttons and lead to ROM. An input stuck high may prevent recovery. Pin tests
must therefore include released buttons, single buttons, pairs, and the full
combination, not just a positive case.

The HYC1 record already persisted in
[mini-codec-hardware.json](../research/mini-codec-hardware.json) reports ROM
PORTA IN=`0x7FF`, DIR=DIE=`0xFFFF`, PU=PD=0. This is useful evidence for the
RAM test: **it does not measure the state after SPL during a cold boot**.
The direction constraint and settling time at that point still need qualification.

## Marker and reset

`reset.S` is separate from the GPIO check. It writes exactly the sixteen bytes
`usb_update_mode\0` to `0x01C7FD80`, executes `csync`, reads `RST_CON` at
`0x10000`, preserves the other bits, and sets bit 4. It executes a second
`csync` and waits for reset.

The string exists both in the MINI application at `0x0203FD2A` and in SPL at
`0x01C05710`. SPL copies it at `0x01C0529A`; its reset at
`0x01C028F4..28FE` sets that exact RST_CON bit. No assumed ROM function address
is used, and no watchdog is armed.

This sequence combines documented elements, but the new marker + RST_CON
body has not yet been physically tested. The MINI application's soft-key uses
a P33 function, and earlier returns from ROM to stock cleared the marker:
these are related tests, not substitutes for the new one. Mailbox retention
and write visibility across reset must also be confirmed on the chosen path.

## Verification and proposed RAM test

```powershell
python -X utf8 firmware/mini/entry_recovery/verify.py
```

The command rebuilds with the vendor assembler and checks the emitted bytes:
636 cases, writes within allowed ranges, restored GPIO, preserved context,
negative branches, and marker/barrier/reset order. The two wait loops with
no external effects are counted algebraically; clocks, silicon, caches, and
switch bounce are not simulated. The full report is
[mini-entry-recovery.json](../research/mini-entry-recovery.json).

ELF `build/mini-entry-recovery/entry-recovery-audit.elf` is an XIP fixture at
`0x02078000`, **not an application or plugin to upload**. That address is
chosen for the audit, not allocated in the formatter. The linker accepts
`--defsym HYPERRIG_ENTRY_GUARD_ADDRESS=...` for a future verified allocation
inside `app.bin`; CRC and encryption must be updated.

A later RAM test may include **only `check.S` and `reset.S`** in a new plugin
within the already allowed slots, with a private stack and an explicit protocol.
`prefix.S` selects G stacks outside the ROM slots and must not execute from
a ROM callback.

1. Plugin entry without GPIO; handshake and payload hash/readback.
2. A register-observation-only command, then a separate command for
   `hyperrig_mini_entry_recovery_check()`: before/after values, result,
   duration, and stack must be recorded. Manual button testing must be
   coordinated with the user. The full loop may be slow at ROM clocks:
   qualify its duration before using it in a command with a short timeout.
3. Only through a distinct command, deliberately call the new marker/reset
   body. A lost USB response neither proves success nor justifies automatic
   retry. A new `4C4A:8057` enumeration and SCSI identity
   `WL82` / `UBOOT1.00` are required.
4. Return to stock through the already verified path; two preset reads must
   match the reference. No NVM write is needed.

The RAM test qualifies GPIO and reset in the ROM context. Prefix and context
correctness remain covered by static audit; cold SPL handover, including
DIR=input, requires separate evidence and must not be claimed as proven by
a USB plugin.

## Effect on the first complete port

The guard specifically addresses a valid G application that enters and then
hangs in clocks, drivers, RTOS, or DSP. Once qualified, it can provide useful
recovery without immediately implementing USB_KEY, while retaining complete
replacement of the MINI application by the adapted G application. Current
offline evidence alone does not remove that gate.

It does not cover an invalid header, corrupted entry or prefix, wrong jump,
interrupted NOR write, damaged SPL, or GPIO fault. A full backup permits
restoration only if a suitable transport remains reachable. Preserved SPL
and OTA increase the options, but their recovery from a damaged application
is not yet physically qualified. USB_KEY remains a possible path independent
of those bytes.

Before relying on the guard for the first update, the indicated tests, exact
preimage integration, and validation/readback of the entire application area
are therefore required. Writer policy, SPL/OTA/data preservation, and handling
an interruption remain separate checks. This work does not access the device
and neither authorises nor performs a flash.
