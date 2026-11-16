# Private stack for the HyperRig ROM probe

The bridge in `firmware/mini/rom_stack/rom_stack_pi32v2.S` lets the new DSP
probe execute a normal C function on a private stack and resume the ROM stack
before calling USB services again. It is **24 bytes, nine instructions**,
with no relocations. It is not a ROM entrypoint or standalone firmware/payload.

```c
int hyperrig_mini_rom_run_on_stack(int (*callback)(void *),
                                 void *argument, void *stack_top);
```

Arguments occupy `r0`, `r1`, `r2`; the callback result returns in `r0`.
The caller must reserve and check the stack, with `stack_top` at the exclusive
upper endpoint and a minimum alignment of four bytes. The probe uses
eight-byte alignment and reserves 4096 bytes. The bridge does not validate
pointers, capacity, or overlap: those checks belong to the linker and verifier
of the payload incorporating it.

| Offset | Bytes | Instruction | Effect |
|---:|---|---|---|
| `00` | `74 04` | `[--sp] = {rets, r4}` | Saves eight bytes on the incoming stack |
| `02` | `64 e0 00 4e` | `r4 = sp` | Preserves the incoming frame pointer |
| `06` | `03 16` | `r3 = r0` | Preserves the callback pointer |
| `08` | `64 e0 80 2e` | `sp = r2` | Selects the private stack |
| `0c` | `10 16` | `r0 = r1` | Passes the argument to the callback |
| `0e` | `c3 00` | `call r3` | Calls a normal C function |
| `10` | `64 e0 80 4e` | `sp = r4` | Resumes the frame on the incoming stack |
| `14` | `34 04` | `{rets, r4} = [sp++]` | Restores SP, RETS, and r4 |
| `16` | `80 00` | `rts` | Returns to the original caller |

The callback must preserve `r4..r15`, finish with a normal return, and not
change execution mode or stack. It must not call ROM services from the new
stack: the probe sends the USB response only after returning. The bridge
preserves the incoming RETS value as well as the return address; arithmetic
conditions and temporary registers `r1..r3` may change as in a normal C call.

## Evidence and verification

The JieLi toolchain pinned to version `20260730.1`, with `-target pi32v2
-mcpu=r3`, assembles the instructions in the table. The verifier also decodes
the bytes with the local ISA table and requires exactly this sequence.
Building a small C example with `__builtin_alloca` independently produces
`r7 = sp`, an SP adjustment, `call r3`, `sp = r7`, and frame restoration.
The compiler therefore already uses the same preserved-register pattern to
save a moving stack. The generated file is
`build/mini-rom-stack/abi_frame.asm`.

Original compiler tests in
[`pi32v2-isa/docs/ABI.md`](../upstream/pi32v2-isa/docs/ABI.md), sections 6.2–6.3,
document frame layout: RETS is at `sp_entrante-4`, the saved register at
`sp_entrante-8`. The same source documents preserved registers, arguments,
result, and alignment. The reference ROM runner
[`runner.S`](../upstream/pi32v2-isa/tools/hwtest/runner.S) saves the incoming
stack, executes cases with another SP, and returns to the runner stack.
These references are pinned in the project lock and their hashes enter the
report; they do not replace a MINI measurement of this new bridge.

```powershell
python tools/verify_mini_rom_stack.py
```

Result: **240 instruction simulations and five negative cases**. The model
checks both slots, four incoming-stack positions, five callback depths up to
4096 bytes, and three return values. It checks preserved registers, return,
the sole eight-byte frame on the incoming stack, and containment of writes
within the private stack. It separately tests both possible interpretations
of SP as an alias of SSP or USP; it does not determine which silicon uses
in this context.

The simulator's callback effect is **a model assuming ABI compliance**, not
execution of the DSP engine. The negative overflow test demonstrates the
model's check, not protection implemented on the target. DSP call-chain depth
and canary checking belong to the separate `rom_engine` probe verification.
The initialisation function's 1228 bytes alone do not establish that the whole
chain fits within 4 KiB.

ELFs `build/mini-rom-stack/audit-*.elf` are linking fixtures only and
**must not be uploaded to the device**. They reserve a 32-byte guard followed
by a 4096-byte stack at each slot's end. Importable function
`validate_stack_layout(base, code_end, guard, bottom,
top)` verifies this contract; `code_end` must include all data and BSS
before the guard, not just code.

## Interrupt state and ROM memory

The bridge emits no explicit writes to SSP, USP, ICFG, exception registers,
clocks, caches, or peripherals, nor `cli`, `sti`, or `rti`.
**This does not imply that SSP remains physically unchanged:** SP can alias
the active stack. The contract is restoration of the incoming SP without
explicitly changing mode or interrupt policy. IRQ behaviour during the private
stack window, possible nesting, and hidden loop state remain to be verified.
No host test simulates them.

The two ranges used as ROM slots are:

| Slot | Range with exclusive upper endpoint | Constraint |
|---|---|---|
| A | `[0x01C20000, 0x01C28000)` | Plugin code, data, BSS, and stack within the same range |
| B | `[0x01C28000, 0x01C30000)` | Same as A; do not overwrite the currently active handler's slot |

The [primary m-bootloader specification](../upstream/m-bootloader/docs/SPEC.md),
sections 2.1, 10.1, and the final limitations table, states that exact bounds
of ROM-owned RAM are unknown. The plugin contract therefore keeps every private
allocation inside its own 32 KiB slot. A NOR backup establishes flash contents,
not dynamic RAM occupancy. A RAM read filled with zeros does not prove a region
is free.

The wider ranges described in the standalone-applications section of the same
specification concern a stage that owns the system. For direct `run-ram` entry,
that path dismantles the ROM environment and ends in reset: it does not provide
a return to ROM USB callbacks. Similarly, regions from `0x01C30000` onward
in the `--app` runner are left free by a specific test application, not by
generic ROM. **No additional free RAM is proven for a MINI plugin that must
return to ROM.**

The verifier executes no USB command, reset, pedal access, or NVM write.
Report [`mini-rom-stack.json`](../research/mini-rom-stack.json) retains
`hardware_execution_verified: false` until a separate test observes the
physical bridge in the new probe.
